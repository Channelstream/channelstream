var gulp = require('gulp');
var path = require('path');
var vulcanize = require('gulp-vulcanize');
var crisper = require('gulp-crisper');

var srcPath = path.join(global.config.demoAppElem.src);
var destPath = path.join(
    global.config.build.rootDirectory,
    global.config.demoAppElem.dest);


function build() {
    return gulp.src(srcPath)
        .pipe(vulcanize({
            inlineScripts: true
        }))
        .pipe(crisper({
            onlyScript: true
        }))
        .pipe(gulp.dest(destPath));
}

module.exports = {
    build: build
};