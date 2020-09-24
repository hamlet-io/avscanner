#!groovy

// Deployment units for this code repo
def deploymentUnits = [
    'avscanner'
]

pipeline {
    agent {
        label 'hamlet-latest'
    }
    options {
        timestamps ()
        buildDiscarder(
            logRotator(
                numToKeepStr: '10'
            )
        )
        disableConcurrentBuilds()
        durabilityHint('PERFORMANCE_OPTIMIZED')
        parallelsAlwaysFailFast()
        skipDefaultCheckout()
        quietPeriod 60
    }

    environment {
        properties_file = '/var/opt/properties/biosecurity.properties'
        slack_channel = '#bio-integration'
    }

    stages {

        stage('Testing') {

            environment {
                COMPOSE_PROJECT_NAME = "${BUILD_TAG}"
                COMPOSE_FILE="docker-compose.yml:docker-compose-ci.yml"
            }

            stages {
                stage('Setup') {
                    steps {
                        dir('test') {
                            script {
                                def codeRepo = checkout scm
                                env["GIT_COMMIT"] = codeRepo.GIT_COMMIT
                            }

                            sh '''#!/bin/bash
                            mkdir --parents ./minio/data/archive
                            mkdir --parents ./minio/data/quarantine
                            mkdir --parents ./minio/data/unprocessed
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir('test') {
                            // running tests using entrypoint-ci.sh as entrypoint script, see docker-compose-ci.yml
                            sh '''#!/bin/bash
                            # Testing
                            docker-compose --no-ansi up --build --remove-orphans --exit-code-from processor 
                            '''
                        }
                    }

                    post {
                        always {
                            dir('test'){
                                script {
                                    def summary = junit 'src/test-report.xml'
                                    env['CHECK_STATUS'] = "FAILURE"
                                    env['TOTAL_COUNT'] = summary.totalCount
                                    env['FAIL_COUNT'] = summary.failCount
                                    env['SKIP_COUNT'] = summary.skipCount
                                    env['PASS_COUNT'] = summary.passCount

                                    env['CHECK_CONCLUSION'] = "SUCCESS"
                                    if (env.FAIL_COUNT.toInteger() != 0) {
                                        env['CHECK_CONCLUSION'] = "FAILURE"
                                    }
                                }

                                publishChecks name: 'Tests', conclusion: "${env.CHECK_CONCLUSION}", title: "Test Summary - ${env.TOTAL_COUNT}, Failures: ${env.FAIL_COUNT}, Skipped: ${env.SKIP_COUNT}, Passed: ${env.PASS_COUNT}", summary: 'test results', text: "Test Summary - ${env.TOTAL_COUNT}, Failures: ${env.FAIL_COUNT}, Skipped: ${env.SKIP_COUNT}, Passed: ${env.PASS_COUNT}"
                                publishCoverage adapters: [coberturaAdapter('src/coverage.xml')]
                            }
                        }
                    }
                }

                stage('Style') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            dir('test') {
                                sh '''#!/bin/bash
                                flake8 --output-file=flake8.txt
                                '''
                            }
                        }
                    }

                    post {
                        always {
                            dir('test') {
                                recordIssues enabledForFailure: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false]], tool: flake8(pattern: 'flake8.txt')
                            }
                        }
                    }
                }
            }

            post {
                failure {
                    slackSend (
                        message: "*Failure* | <${BUILD_URL}|${JOB_NAME}> \n Testing stage",
                        channel: "${env["slack_channel"]}",
                        color: "#D20F2A"
                    )
                }
                cleanup {
                    dir('test') {
                        sh '''#!/bin/bash
                        if [[ -n "${COMPOSE_FILE}" ]]; then
                            docker-compose down --rmi local -v --remove-orphans
                        fi
                        '''
                    }
                }
            }
        }

        stage('continuous deploy') {
            when {
                anyOf {
                    branch 'master'
                    branch 'cd_*'
                }
            }

            environment {
                ENVIRONMENT = 'integration'
                PRODUCT_INFRASTRUCTURE_REFERENCE = 'master'
                PRODUCT_CONFIG_REFERENCE = 'master'
                GENERATION_CONTEXT_DEFINED = ''
                DEPLOYMENT_UNITS = "${deploymentUnits.join(",")}"

                IMAGE_FORMAT = 'docker'
                BUILD_PATH = ''
                DOCKER_CONTEXT_DIR = 'build'
                BUILD_SRC_DIR = ''
                DOCKER_FILE = "build/devops/docker/Dockerfile"

                product_cmdb = 'https://github.com/gs-dawr/biosecurity-cmdb'
                GITHUB_CREDENTIALS = credentials('github')
            }

            steps {

                // Product Setup
                dir('.hamlet/product') {
                    git(
                        url: "${env["product_cmdb"]}",
                        credentialsId: 'github',
                        changelog: false,
                        poll: false
                    )

                    // Load in Properties files
                    script {
                        def productProperties = readProperties interpolate: true, file: "${env.properties_file}";
                        productProperties.each{ k, v -> env["${k}"] ="${v}" }

                    }
                }

                dir('build') {
                    checkout scm
                }

                sh '''#!/bin/bash
                    ${AUTOMATION_BASE_DIR}/setContext.sh
                '''

                script {
                    def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                    contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                }

                sh '''#!/bin/bash
                    ${AUTOMATION_DIR}/constructTree.sh
                '''

                script {
                    def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                    contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                }

                sh '''#!/bin/bash
                    ${AUTOMATION_DIR}/manageImages.sh

                '''

                script {
                    def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                    contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                }

                build job: "../../deploy/${env["ENVIRONMENT"]}-deploy", wait: false, parameters: [
                    string(name: 'DEPLOYMENT_UNITS', value: "${env["DEPLOYMENT_UNITS"]}" ),
                    string(name: 'GIT_COMMIT', value: "${env["GIT_COMMIT"]}"),
                    string(name: 'IMAGE_FORMATS', value: "${env["IMAGE_FORMAT"]}" )
                ]
            }

            post {
                success {
                    slackSend (
                        message: "*Success* | <${BUILD_URL}|${JOB_NAME}> \n CD deployment started",
                        channel: "${env["slack_channel"]}",
                        color: "#50C878"
                    )
                }
            }

        }

        stage('release') {
            when {
                buildingTag()
            }

            environment {
                ENVIRONMENT = 'production'
                DEPLOYMENT_UNITS = "${deploymentUnits.join(",")}"
            }

            steps {
                script {

                    releaseTag = env["TAG_NAME"] ?: env["GIT_COMMIT"].take(7)
                    prepareUnits = ""
                    (env.DEPLOYMENT_UNITS).split(",").each{ i -> prepareUnits = prepareUnits + "${i}!${env["GIT_COMMIT"]}\n"  }

                    build job: "../../deploy/${env["ENVIRONMENT"]}-prepare", wait: true, parameters: [
                        string(name: 'DEPLOYMENT_UNITS', value: "${prepareUnits}" ),
                        string(name: 'RELEASE_IDENTIFIER', value: "${releaseTag}_${currentBuild.timeInMillis}"),
                    ]

                    build job: "../../deploy/${env["ENVIRONMENT"]}-deploy", wait: true, parameters: [
                        string(name: 'DEPLOYMENT_UNITS', value: "${env["DEPLOYMENT_UNITS"]}" ),
                        string(name: 'RELEASE_IDENTIFIER', value: "${releaseTag}_${currentBuild.timeInMillis}"),
                    ]
                }
            }

            post {
                success {
                    slackSend (
                        message: "*Success* | <${BUILD_URL}|${JOB_NAME}> \n Release to ${env["ENVIRONMENT"]} completed",
                        channel: "${env["slack_channel"]}",
                        color: "#50C878"
                    )
                }
            }
        }
    }

    post {
        cleanup {
            cleanWs()
        }
    }
}