/*
 * Copyright 2015 Telefónica I+D
 * All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
'use strict';

/**
 * Grunt tasks definitions
 *
 * @param {Object} grunt
 */
module.exports = function (grunt) {

    grunt.initConfig({

        pkgFile: 'package.json',
        pkg: grunt.file.readJSON('package.json'),

        dirs: {
            lib: ['lib'],
            test: ['test'],
            reportTest: ['report/test'],
            reportLint: ['report/lint'],
            reportCoverage: ['report/coverage'],
            siteCoverage: ['site/coverage'],
            siteReport: ['site/report'],
            siteDoc: ['site/doc']
        },

        clean: {
            reportTest: ['<%= dirs.reportTest[0] %>'],
            reportLint: ['<%= dirs.reportLint[0] %>'],
            reportCoverage: ['<%= dirs.reportCoverage[0] %>'],
            lcovCoverage: ['<%= dirs.siteCoverage[0] %>'],
            siteCoverage: ['<%= dirs.siteCoverage[0] %>'],
            siteReport: ['<%= dirs.siteReport[0] %>'],
            siteDoc: ['<%= dirs.siteDoc[0] %>']
        },

        mkdir: {
            reportTest: {
                options: {
                    create: ['<%= dirs.reportTest[0] %>']
                }
            },
            reportLint: {
                options: {
                    create: ['<%= dirs.reportLint[0] %>']
                }
            },
            reportCoverage: {
                options: {
                    create: ['<%= dirs.reportCoverage[0] %>']
                }
            },
            lcovCoverage: {
                options: {
                    create: ['<%= dirs.siteCoverage[0] %>']
                }
            },
            siteCoverage: {
                options: {
                    create: ['<%= dirs.siteCoverage[0] %>']
                }
            },
            siteDoc: {
                options: {
                    create: ['<%= dirs.siteDoc[0] %>']
                }
            },
            siteReport: {
                options: {
                    create: ['<%= dirs.siteReport[0] %>']
                }
            }
        },

        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            gruntfile: {
                src: 'Gruntfile.js'
            },
            lib: {
                src: ['<%= dirs.lib[0] %>/**/*.js']
            },
            test: {
                src: ['<%= dirs.test[0] %>/unit/*.js']
            },
            reportGruntfile: {
                src: 'Gruntfile.js',
                options: {
                    reporter: 'checkstyle',
                    reporterOutput: '<%= dirs.reportLint[0] %>/jshint-gruntfile.xml'
                }
            },
            reportLib: {
                src: '<%= dirs.lib[0] %>/**/*.js',
                options: {
                    reporter: 'checkstyle',
                    reporterOutput: '<%= dirs.reportLint[0] %>/jshint-lib.xml'
                }
            },
            reportTest: {
                src: '<%= dirs.test[0] %>/unit/*.js',
                options: {
                    reporter: 'checkstyle',
                    reporterOutput: '<%= dirs.reportLint[0] %>/jshint-test.xml'
                }
            }
        },

        watch: {
            gruntfile: {
                files: '<%= jshint.gruntfile.src %>',
                tasks: ['jshint:gruntfile']
            },
            lib: {
                files: '<%= jshint.lib.src %>',
                tasks: ['jshint:lib', 'test']
            },
            test: {
                files: '<%= jshint.test.src %>',
                tasks: ['jshint:test', 'test']
            }
        },

        env: {
            testReport: {
                NODE_ENV: 'production',
                XUNIT_FILE: '<%= dirs.reportTest[0] %>/TEST-xunit.xml'
            }
        },

        mochaTest: {
            unit: {
                options: {
                    ui: 'tdd',
                    reporter: 'spec',
                    timeout: 30000,
                    ignoreLeaks: false
                },
                src: [
                    '<%= jshint.test.src %>'
                ]
            },
            unitReport: {
                options: {
                    ui: 'tdd',
                    reporter: 'xunit-file',
                    quiet: true

                },
                src: [
                    '<%= jshint.test.src %>'
                ]
            }
        },

        dox: {
            options: {
                title: 'Fiware health Documentation'
            },
            files: {
                src: ['<%= jshint.lib.src %>', '<%= jshint.test.src %>'],
                dest: '<%= dirs.siteDoc[0] %>'
            }
        },

        exec: {
            istanbul: {
                cmd: 'bash -c "./node_modules/.bin/istanbul cover ' +
                    '-x "<%= dirs.test[0] %>" ' +
                    '-x "<%= dirs.lib[0] %>/public" ' +
                    '-x "<%= dirs.lib[0] %>/oauth2.js" ' +
                    '-x "<%= dirs.lib[0] %>/views" ' +
                    '--root <%= dirs.lib[0] %>/ ' +
                    '--dir <%= dirs.reportCoverage[0] %> -- ' +
                    '\\"`npm root -g`/grunt-cli/bin/grunt\\" test >/dev/null && ' +
                    'mv <%= dirs.reportCoverage[0] %>/lcov-report <%= clean.lcovCoverage[0] %> && ' +
                    './node_modules/.bin/istanbul report --dir <%= dirs.reportCoverage[0] %> text-summary"'
            },
            istanbulCobertura: {
                cmd: 'bash -c "./node_modules/.bin/istanbul report --dir <%= dirs.reportCoverage[0] %> cobertura"'
            }
        },

        plato: {
            options: {
                jshint: grunt.file.readJSON('.jshintrc')
            },
            lib: {
                files: {
                    '<%= clean.siteReport[0] %>': '<%= jshint.lib.src %>'
                }
            }
        },

        gjslint: {
            options: {
                reporter: {
                    name: 'console'
                },
                flags: [
                    '--flagfile .gjslintrc' //use flag file
                ],
                force: false
            },
            gruntfile: {
                src: '<%= jshint.gruntfile.src %>'
            },
            lib: {
                src: '<%= jshint.lib.src %>'
            },
            test: {
                src: '<%= jshint.test.src %>'
            },
            report: {
                options: {
                    reporter: {
                        name: 'gjslint_xml',
                        dest: '<%= clean.reportLint[0] %>/gjslint.xml'
                    },
                    flags: [
                        '--flagfile .gjslintrc'
                    ],

                    force: false
                },
                src: ['<%= jshint.gruntfile.src %>', '<%= jshint.lib.src %>', '<%= jshint.test.src %>']
            }
        }
    });

    // These plugins provide necessary tasks.
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-mocha-test');
    grunt.loadNpmTasks('grunt-env');
    grunt.loadNpmTasks('grunt-exec');
    grunt.loadNpmTasks('grunt-plato');
    grunt.loadNpmTasks('grunt-gjslint');
    grunt.loadNpmTasks('grunt-dox');
    grunt.loadNpmTasks('grunt-mkdir');

    grunt.registerTask('test', 'Run tests',
        ['mochaTest:unit']);

    grunt.registerTask('test-report', 'Generate tests reports',
        ['env', 'clean:reportTest', 'mkdir:reportTest', 'mochaTest:unitReport']);

    grunt.registerTask('coverage', 'Print coverage summary',
        ['clean:lcovCoverage', 'mkdir:lcovCoverage', 'exec:istanbul']);

    grunt.registerTask('coverage-report', 'Generate Cobertura report',
        ['clean:reportCoverage', 'mkdir:reportCoverage', 'coverage', 'exec:istanbulCobertura']);

    grunt.registerTask('complexity', 'Generate code complexity reports', ['plato']);

    grunt.registerTask('doc', 'Generate source code JSDoc', ['dox']);

    grunt.registerTask('lint-jshint', 'Check source code style with JsHint',
        ['jshint:gruntfile', 'jshint:lib', 'jshint:test']);

    grunt.registerTask('lint-gjslint', 'Check source code style with Google Closure Linter',
        ['gjslint:gruntfile', 'gjslint:lib', 'gjslint:test']);

    grunt.registerTask('lint', 'Check source code style', ['lint-jshint', 'lint-gjslint']);

    grunt.registerTask('lint-report', 'Generate checkstyle reports',
        ['clean:reportLint', 'mkdir:reportLint', 'jshint:reportGruntfile', 'jshint:reportLib',
            'jshint:reportTest', 'gjslint:report']);

    grunt.registerTask('site', ['doc', 'coverage', 'complexity']);

    // Default task.
    grunt.registerTask('default', ['lint-jshint', 'test']);

};
