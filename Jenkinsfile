pipeline {
    agent any
    environment {
        IMAGE = 'lukaknezevic/cicd-pipeline-demo'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Build') {
            agent {
                docker {
                    image 'node:20-alpine'
                    reuseNode true
                }
            }
            steps {
                sh 'npm install'
            }
        }
        stage('Test') {
            agent {
                docker {
                    image 'node:20-alpine'
                    reuseNode true
                }
            }
            steps {
                sh 'npm test'
            }
        }
        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE}:${BUILD_NUMBER} -t ${IMAGE}:latest ."
            }
        }
        stage('Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh 'echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin'
                    sh "docker push ${IMAGE}:${BUILD_NUMBER}"
                    sh "docker push ${IMAGE}:latest"
                    sh 'docker logout'
                }
            }
        }
        stage('Deploy') {
            steps {
                sshagent(credentials: ['deploy-target-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no root@deploy-target '
                            docker pull ${IMAGE}:latest &&
                            docker stop app || true &&
                            docker rm app || true &&
                            docker run -d --name app -p 3000:3000 ${IMAGE}:latest
                        '
                    """
                }
            }
        }
    }
}
