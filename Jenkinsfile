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
                    sh 'printf "%s" "$DH_PASS" | docker login -u "$DH_USER" --password-stdin'
                    sh "docker push ${IMAGE}:${BUILD_NUMBER}"
                    sh "docker push ${IMAGE}:latest"
                    sh 'docker logout'
                }
            }
        }
        stage('Deploy to AWS') {
            steps {
                withCredentials([string(credentialsId: 'ec2-host', variable: 'EC2_HOST')]) {
                    sshagent(credentials: ['aws-ec2-ssh-key']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@\$EC2_HOST '
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
        stage('Health check') {
            agent {
                docker {
                    image 'python:3.12-alpine'
                    reuseNode true
                }
            }
            steps {
                withCredentials([string(credentialsId: 'ec2-host', variable: 'EC2_HOST')]) {
                    sh 'python scripts/health_check.py "http://$EC2_HOST:3000/health" 10 3'
                }
            }
        }
    }
}
