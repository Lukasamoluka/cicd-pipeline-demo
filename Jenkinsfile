pipeline {
    agent any
	options {
        skipDefaultCheckout(true)
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
	   steps {
                sh 'npm install'
            }
        }
    }
}



















