pipeline {
    parameters {
        string(name: 'Cloud', defaultValue: 'none', description: 'Which cloud from platforms.yml do you want to build on?')
        string(name: 'Cloud_type', defaultValue: 'none', description: 'What is the cloud type?')
        string(name: 'Template', defaultValue: 'none', description: 'Which template do you want to build?')

    }

    agent {
        label 'build'
    }

    options {
        ansiColor('xterm')
        timestamps()
    }

    stages {
        stage('Build template on cloud') {
            steps {
                script {
                    retry (3) {
                        try {
                            timeout(activity: true, time: 3, unit: 'HOURS') {

                                echo "Build ${params.Template} on ${params.Cloud}"

                                sh "export ANSIBLE_FORCE_COLOR=true && \
                                    ansible-playbook -vv \
                                                    -i inventories/image-factory/hosts \
                                                    -e \"cloud=${params.Cloud}\" \
                                                    -e \"cloud_type=${params.Cloud_type}\" \
                                                    -e \"template=${params.Template}\" \
                                                    --vault-password-file ~/.ansible/vaultpass.txt \
                                                    playbooks/main.yml"
                            }
                        }
                        catch (exception) {
                            throw exception
                        }

                        finally {
                            sh "export ANSIBLE_FORCE_COLOR=true && \
                                ansible-playbook -vv \
                                                -i inventories/image-factory/hosts \
                                                -e \"cloud=${params.Cloud}\" \
                                                -e \"cloud_type=${params.Cloud_type}\" \
                                                -e \"template=${params.Template}\" \
                                                --vault-password-file ~/.ansible/vaultpass.txt \
                                                playbooks/cleanup.yml"
                        }
                    }
                }
            }
        }
    }
}
