pipeline {
    agent any
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
    }
}



















