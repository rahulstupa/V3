'use strict';

module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    jshint: {
      options: {
        globals: {
          'require': true,
          'define': true,
          'module': true
        },
        trailing: true, // prevent trailing whitespace.
        curly: true,
        undef: true,
        unused: true,
        browser: true,
        es3: true // prevent trailing commas.
      },
      build: {
        files: {
          src: ['lib/**/*.js']
        }
      }
    },

    bump: {
      options: {
        files: ['package.json', 'bower.json'],
        updateConfigs: ['pkg'],
        commit: true,
        commitMessage: 'Release v%VERSION%',
        commitFiles: ['package.json', 'bower.json', 'CHANGELOG.md'], // '-a' for all files
        createTag: true,
        tagName: 'v%VERSION%',
        tagMessage: 'Version %VERSION%',
        push: true,
        pushTo: 'origin',
        gitDescribeOptions: '--tags --always --abbrev=1 --dirty=-d' // options to use with '$ git describe'
      }
    },

    conventionalChangelog: {
      options: {
        changelogOpts: {
          // conventional-changelog options go here
        },
        context: {
          // context goes here
        },
        gitRawCommitsOpts: {
          // git-raw-commits options go here
        },
        parserOpts: {
          // conventional-commits-parser options go here
        },
        writerOpts: {
          // conventional-changelog-writer options go here
        }
      },
      release: {
        src: 'CHANGELOG.md'
      }
    },
  });

  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-bump');
  grunt.loadNpmTasks('grunt-conventional-changelog');

  grunt.registerTask('default', ['build']);
  grunt.registerTask('build', ['jshint']);
  grunt.registerTask('changelog', ['conventionalChangelog']);

};
