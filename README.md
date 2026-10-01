# Automated CI/CD Deployment Pipeline

A hands-on DevOps portfolio project demonstrating an end-to-end automated deployment pipeline: from a `git push` to a running containerized application on a target server — fully orchestrated by Jenkins.

## Why this project

This project ties together everything learned during a structured DevOps self-study path (Linux fundamentals → Git → Docker → Jenkins), building on hands-on experience from KodeKloud labs and prior IT operations/NOC background. It's the first practical project in a broader learning roadmap:

**Jenkins/CI-CD → Kubernetes → Ansible → Terraform → Prometheus/Grafana → AWS**

The goal is to build a working, documented, real pipeline — not just complete isolated exercises — before moving on to Kubernetes (where the SSH deploy stage here will later be upgraded to a Kubernetes cluster deploy).

## Status: fully working end to end

A `git push` to `main` automatically triggers Jenkins (via a GitHub webhook), which builds, tests, packages, and deploys the application to a simulated production server — no manual steps required.

## Tech stack

| Tool | Role |
|---|---|
| **Linux (WSL2 / Ubuntu)** | Local development & container host environment |
| **Git & GitHub** | Version control, source of truth, webhook trigger |
| **Docker** | Application containerization + simulated deploy target |
| **Jenkins** | CI/CD orchestration (declarative pipeline) |
| **Docker Hub** | Image registry (push from Jenkins, pull on deploy target) |
| **ngrok** | Tunnels local Jenkins so GitHub webhooks can reach it |

## Architecture / Flow

```
Developer push → GitHub repo
      ↓ (webhook via ngrok)
   Jenkins pipeline triggers
      ↓
 Checkout → Build → Test → Docker Build → Push to Docker Hub
      ↓
 SSH Deploy → Target container pulls new image → restarts app
```

**Jenkins** runs as a container built from a custom image (`jenkins/jenkins:lts` plus the Docker CLI). The host's Docker socket is mounted into it, so pipeline stages can start throw-away containers and build images using the host's Docker engine. Jenkins data lives in a named volume (`jenkins_home`), so jobs and credentials survive container rebuilds.

**Deploy target:** a Docker container simulating a production host — Ubuntu with OpenSSH (key-based auth only) plus the Docker CLI and the host's Docker socket mounted in, so it can pull and run the application image itself. Jenkins and the deploy target share a Docker network (`cicd-net`) so they can reach each other by container name.

**Automatic trigger:** a GitHub webhook (`/github-webhook/`) calls Jenkins through an ngrok tunnel on every push, so no one has to click "Build Now" manually.

## Pipeline stages (Jenkinsfile)

| # | Stage | What it does |
|---|---|---|
| 1 | **Checkout** | Pull latest code from GitHub |
| 2 | **Build** | `npm install` inside a temporary `node:20-alpine` container |
| 3 | **Test** | `npm test` (Node's built-in test runner) checks that `/health` returns `{"status":"healthy"}` |
| 4 | **Docker Build** | Build the image, tagged with the build number and `latest` |
| 5 | **Push** | Push both tags to Docker Hub |
| 6 | **Deploy** | SSH into the deploy target; pull the new image; stop/remove the old `app` container; start the new one; retry a `/health` check (up to 10 times, 2s apart) before declaring success |

Build and Test run in disposable Node containers (`agent { docker { image 'node:20-alpine' reuseNode true } }`), so Jenkins itself needs no Node.js installation. `reuseNode true` shares the workspace between stages, so the packages installed in Build are available to Test. Docker Build, Push and Deploy run directly on the Jenkins agent, using the Docker CLI added to the custom Jenkins image.

Secrets (Docker Hub token, SSH private key) are stored as Jenkins credentials and referenced by ID (`dockerhub-creds`, `deploy-target-ssh-key`) — never written in the Jenkinsfile itself, since it lives in a public GitHub repo.

## Setup progress log

- [x] Defined project scope and architecture
- [x] Confirmed local environment: WSL2 (Ubuntu) + Docker Desktop with WSL integration
- [x] Project structure (Express app + Dockerfile)
- [x] Built and ran the app as a Docker image, verified locally
- [x] Deploy target container (SSH server + Docker CLI), tested with key-based login and `docker` commands over SSH
- [x] Jenkins container with Docker CLI and Docker socket access, Docker Pipeline and SSH Agent plugins installed
- [x] Jenkins credentials (Docker Hub token, SSH key for the deploy target)
- [x] GitHub repository created and connected to a Jenkins Pipeline job (Pipeline script from SCM)
- [x] Full Jenkinsfile: Checkout, Build, Test, Docker Build, Push, Deploy — all passing
- [x] ngrok tunnel + GitHub webhook — push triggers a build automatically
- [x] End-to-end test: code change → push → automatic build → automatic deploy, confirmed working
- [x] Post-deploy health check: Deploy stage retries `/health` after starting the new container, so the pipeline confirms the app is actually responding — not just that the container started
- [ ] *(Stretch goal)* Rollback logic on failed deploy
- [ ] *(Stretch goal)* Slack notification on build status

## Known limitations

- **ngrok free tier:** generates a new public URL every time the tunnel restarts, so the GitHub webhook's Payload URL has to be updated manually after every ngrok restart. A paid ngrok plan (or a real public server, later in the roadmap) would give a fixed URL.
- **`--user root` on Jenkins and root SSH on the deploy target:** acceptable for a local, single-user demo, but not how this would be set up in a real environment (least-privilege users, restricted sudo/Docker group access instead).

## Troubleshooting notes

Real issues hit during development — kept here as a log of what went wrong and how it was diagnosed/fixed (useful both as a personal reference and to show problem-solving process).

**1. App unreachable from the browser after `docker run`**
- Symptom: container showed "Up" and logs confirmed `App listening on port 3000`, but requests just hung.
- Root cause #1: Express's `app.listen(PORT, ...)` wasn't bound to `0.0.0.0`, so it didn't accept connections from outside the container. Fixed by binding explicitly: `app.listen(PORT, '0.0.0.0', ...)`.
- Root cause #2: a broken **WSL2 → Windows localhost forwarding** link (`curl` worked from inside WSL, but not from Windows). Fixed with `wsl --shutdown` (as Administrator), which forces WSL2 to fully restart its virtual network adapter.

**2. SSH deploy-target container exited immediately**
- Symptom: `docker ps` showed the container gone seconds after `docker run`.
- Root cause: `sshd` needs `/run/sshd`, normally created by systemd, which containers don't have.
- Fix: added `RUN mkdir -p /run/sshd` to the Dockerfile.

**3. Jenkins had no Docker and no Node.js**
- Root cause: the stock Jenkins image is an empty environment — no build tools, no connection to a Docker engine.
- Fix: built a custom Jenkins image with the Docker CLI copied in, and mounted `/var/run/docker.sock` when recreating the container (keeping the `jenkins_home` volume, so nothing was lost). Node.js stays out of Jenkins entirely — Build and Test run in a temporary `node:20-alpine` container instead.

**4. `fatal: not in a git directory` when Jenkins read the Jenkinsfile from GitHub**
- Root cause: after switching the Jenkins container to run as root, file ownership in the workspace volume no longer matched, and Git refuses to work in directories it considers to have "dubious ownership".
- Fix: `docker exec jenkins git config --global --add safe.directory '*'` (fine for a local demo; a real setup would fix ownership instead).

**5. A test that would have hung the pipeline**
- Problem: `app.js` started the server as soon as it was loaded (`app.listen` ran on import), so a test importing it would either hang forever or collide with another instance on port 3000.
- Fix: the app is exported with `module.exports = app`, and only starts listening when the file is run directly (`if (require.main === module)`). The test starts its own server on a random free port (`app.listen(0)`) and shuts it down when finished.

**6. Docker Hub login failing with `malformed HTTP Authorization header`**
- Symptom: `docker login` failed with this error both inside the Jenkins pipeline and when tested manually from the host — ruling out anything Jenkins-specific.
- Root cause: the Docker Hub account no longer accepts a plain password for `docker login` from the CLI; only a Personal Access Token works.
- Fix: generated a Docker Hub Access Token and used it as the password in the Jenkins credential.

**7. Jenkins credentials not found (`dockerhub-creds`, `deploy-target-ssh-key`)**
- Root cause: when the credentials were first created, the **ID** field was left blank, so Jenkins auto-generated a random ID (e.g. the account username, or a UUID) instead of the ID referenced in the Jenkinsfile.
- Fix: deleted and recreated each credential, explicitly setting the ID field this time. (The ID can't be edited on an existing credential — only the content can; changing the ID requires delete + recreate.)

**8. SSH Agent plugin failing to load the private key (`error in libcrypto`)**
- Root cause: the key generated by `ssh-keygen` was in the newer OpenSSH key format, which the SSH Agent plugin's `ssh-add` couldn't parse.
- Fix: converted the key to the classic PEM format without regenerating it: `ssh-keygen -p -m PEM -f deploy_key -N ""`. Updated the Jenkins credential with the new key content.

**9. GitHub webhook delivered but Jenkins never started a build**
- Root cause: the "GitHub hook trigger for GITScm polling" checkbox in the job's Build Triggers wasn't enabled, so Jenkins ignored an otherwise successfully delivered webhook.
- Fix: enabled it in the job configuration. (A push made before this fix understandably didn't trigger anything — the webhook was delivered, but nothing was listening for it.)

**10. Health check passing `curl` from the host but failing `wget` inside the container**
- Symptom: after adding a post-deploy health check (`docker exec app wget -qO- http://localhost:3000/health`), every one of the 10 retry attempts failed with "Connection refused" — even though `curl http://localhost:3000/health` from the host worked instantly, and the container showed as healthy and running.
- Diagnosis: `docker exec app which wget` confirmed `wget` existed in the container; running it manually reproduced the same "Connection refused".
- Root cause: the same class of issue as the very first WSL networking bug — `localhost` inside the Alpine container's `wget` resolved to the IPv6 loopback (`::1`), and the app wasn't accepting connections on that address.
- Fix: changed the health check URL from `http://localhost:3000/health` to `http://127.0.0.1:3000/health`, forcing IPv4. No app code changes needed.

## Application

Simple Node.js Express "hello world" API with `/` and `/health` routes, plus one automated test for `/health` — kept minimal on purpose, since the focus of this project is the **pipeline and infrastructure**, not the application logic.

## Repository

[github.com/Lukasamoluka/cicd-pipeline-demo](https://github.com/Lukasamoluka/cicd-pipeline-demo)

---
*This document is a living log — updated as the project progresses.*
