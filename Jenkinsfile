#!groovy

// Deployment units for this code repo
def deploymentUnits = [
    'processor-v1-validator', 'processor-v1-avscanner', 'processor-v1-archiver'
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
        DOCKER_STAGE_DIR = '/temp/docker'
        DOCKER_BUILD_DIR = "${env.DOCKER_STAGE_DIR}/${BUILD_TAG}"

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
                        dir("${env.DOCKER_BUILD_DIR}") {
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
                        dir("${env.DOCKER_BUILD_DIR}") {
                            sh '''#!/bin/bash
                            # Testing
                            docker-compose --no-ansi up --build --remove-orphans --exit-code-from processor
                            '''
                        }
                    }

                    post {
                        always {
                            dir("${env.DOCKER_BUILD_DIR}"){
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
                                /*publishCoverage adapters: [coberturaAdapter('src/coverage.xml')]*/
                            }
                        }
                    }
                }

                /*stage('Style') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            dir("${env.DOCKER_BUILD_DIR}") {
                                sh '''#!/bin/bash
                                docker-compose run django flake8 --output-file=flake8.txt
                                '''
                            }
                        }
                    }

                    post {
                        always {
                            dir("${env.DOCKER_BUILD_DIR}") {
                                recordIssues enabledForFailure: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false]], tool: flake8(pattern: 'src/flake8.txt')
                            }
                        }
                    }
                }*/
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
                    dir("${env.DOCKER_BUILD_DIR}") {
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
        stage('utility - CloudwatchSlack' ) {

            // we always force the cloudwatch slack instance since it doesn't change much
            when {
                equals expected: true, actual: params.force_cloudwatch_slack
            }

            environment {
                //hamlet deployment variables
                deployment_units = 'alert-slack'
                segment = 'default'
                image_format = 'lambda'

                GENERATION_CONTEXT_DEFINED = ''

                BUILD_PATH = "build/cloudwatch-slack"
                BUILD_SRC_DIR = ''
            }

            steps {

                dir('build/cloudwatch-slack') {
                    script {
                        def repo = git changelog: false, poll: false, url: 'https://github.com/codeontap/lambda-cloudwatch-slack'
                        env['GIT_COMMIT'] = repo.GIT_COMMIT
                    }

                    sh '''#!/bin/bash
                        npm ci
                        npx serverless package

                        if [[ -f .serverless/cloudwatch-slack.zip ]]; then
                            mkdir -p dist
                            cp .serverless/cloudwatch-slack.zip dist/lambda.zip
                        else
                            echo "lambda not found!!!"
                            exit 255
                        fi
                    '''

                    script {
                        def contextProperties = readProperties interpolate: true, file: "${properties_file}" ;
                        contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                    }

                    sh '''#!/bin/bash
                    ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                    '''

                    script {
                        def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                        contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                    }

                    sh '''#!/bin/bash
                    ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -u "${deployment_units}" -f "${image_format}"  || exit $?
                    '''

                    script {
                        def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                        contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                    }

                    build job: '../../deploy/integration-deploy', wait: false, parameters: [
                        extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.deployment_units}"),
                        string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                        booleanParam(name: 'AUTODEPLOY', value: true),
                        string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                        string(name: 'SEGMENT', value: "${env.segment}" )
                    ]

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