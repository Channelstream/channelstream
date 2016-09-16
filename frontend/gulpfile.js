/**
 * @license
 * Copyright (c) 2016 The Polymer Project Authors. All rights reserved.
 * This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
 * The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
 * The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
 * Code distributed by Google as part of the polymer project is also
 * subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
 */

'use strict';

const path = require('path');
const gulp = require('gulp');
const gulpif = require('gulp-if');

// Got problems? Try logging 'em
// const logging = require('plylog');
// logging.setVerbose();

// !!! IMPORTANT !!! //
// Keep the global.config above any of the gulp-tasks that depend on it
global.config = {
    polymerJsonPath: path.join(process.cwd(), 'polymer.json'),
    build: {
        rootDirectory: 'build',
        bundledDirectory: 'bundled',
        unbundledDirectory: 'unbundled',
        // Accepts either 'bundled', 'unbundled', or 'both'
        // A bundled version will be vulcanized and sharded. An unbundled version
        // will not have its files combined (this is for projects using HTTP/2
        // server push). Using the 'both' option will create two output projects,
        // one for bundled and one for unbundled
        bundleType: 'both'
    },
    backendStaticsDirectory: '../channelstream/static',
    // Path to your service worker, relative to the build root directory
    serviceWorkerPath: 'service-worker.js',
    // Service Worker precache options based on
    // https://github.com/GoogleChrome/sw-precache#options-parameter
    swPrecacheConfig: {
        navigateFallback: '/index.html'
    },
    // changed: ergo
    src: 'src',
    adminViewElem: {
        src: 'src/channelstream-admin/channelstream-admin.html',
        dest: 'channelstream-admin'
    },
    demoAppElem: {
        src: 'src/channelstream-demo/channelstream-chat-demo/channelstream-chat-demo.html',
        dest: 'channelstream-demo'
    }
};

// Add your own custom gulp tasks to the gulp-tasks directory
// A few sample tasks are provided for you
// A task should return either a WriteableStream or a Promise
const clean = require('./gulp-tasks/clean.js');
// const images = require('./gulp-tasks/images.js');
// const project = require('./gulp-tasks/project.js');
const adminView = require('./gulp-tasks/vulcanized-admin.js');
const demoApp = require('./gulp-tasks/vulcanized-demo.js');

// The source task will split all of your source files into one
// big ReadableStream. Source files are those in src/** as well as anything
// added to the sourceGlobs property of polymer.json.
// Because most HTML Imports contain inline CSS and JS, those inline resources
// will be split out into temporary files. You can use gulpif to filter files
// out of the stream and run them through specific tasks. An example is provided
// which filters all images and runs them through imagemin
function source() {
    return project.splitSource()
    // Add your own build tasks here!
        .pipe(gulpif('**/*.{png,gif,jpg,svg}', images.minify()))
        .pipe(project.rejoin()); // Call rejoin when you're finished
}

// The dependencies task will split all of your bower_components files into one
// big ReadableStream
// You probably don't need to do anything to your dependencies but it's here in
// case you need it :)
function dependencies() {
    return project.splitDependencies()
        .pipe(project.rejoin());
}

// Clean the build directory, split all source and dependency files into streams
// and process them, and output bundled and unbundled versions of the project
// with their own service workers
// changed: ergo
// gulp.task('default', gulp.series([
//   clean.build,
//   project.merge(source, dependencies),
//   project.serviceWorker
// ]));

// Rerun the task when a file changes
var notifyWatch = function (filepath) {
    console.log('File ' + filepath + ' was changed running tasks...');
};

gulp.task('watch', function () {
    var jsWatcher = gulp.watch('src/**/*.js', gulp.series('default'));
    var htmlWatcher = gulp.watch('src/**/*.html', gulp.series('default'))
    jsWatcher.on('change', notifyWatch);
    htmlWatcher.on('change', notifyWatch);
});





function copy_build() {
    return gulp.src(global.config.build.rootDirectory + '/**')
        .pipe(gulp.dest(global.config.backendStaticsDirectory));
}

gulp.task('default', gulp.series([
    clean.build,
    adminView.build,
    demoApp.build,
    copy_build
]))