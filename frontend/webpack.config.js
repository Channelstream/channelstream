var HtmlWebpackPlugin = require('html-webpack-plugin');
var CopyWebpackPlugin = require('copy-webpack-plugin');
var webpackUglifyJsPlugin = require('webpack-uglify-js-plugin');
var path = require('path');

let CHANNELSTREAM_STATIC = path.resolve(__dirname, '../channelstream/static/');

console.error(CHANNELSTREAM_STATIC);


let configFactory = (name, suffix = null, babelConfig) => {
    let subext = suffix ? `.${suffix}` : '';
    return {
        name: name,
        // Tell Webpack which file kicks off our app.
        entry: {
            admin: path.resolve(__dirname, 'src/channelstream-admin/index.js')
        },
        // Tell Weback to output our bundle to ./dist/bundle.js
        output: {
            filename: `channelstream-[name]${subext}.js`,
            path: path.resolve(__dirname, 'dist')
        },
        // Tell Webpack which directories to look in to resolve import statements.
        // Normally Webpack will look in node_modules by default but since we’re overriding
        // the property we’ll need to tell it to look there in addition to the
        // bower_components folder.
        resolve: {
            modules: [
                path.resolve(__dirname, 'node_modules')
            ]
        },
        // These rules tell Webpack how to process different module types.
        // Remember, *everything* is a module in Webpack. That includes
        // CSS, and (thanks to our loader) HTML.
        module: {
            rules: [
                {
                    // If you see a file that ends in .js, just send it to the babel-loader.
                    test: /\.js$/,
                    use: {
                        loader: 'babel-loader',
                        options: babelConfig
                    }
                }
            ]
        },
        plugins: [
            // This plugin will copy files over to ‘./dist’ without transforming them.
            // That's important because the custom-elements-es5-adapter.js MUST
            // remain in ES2015. We’ll talk about this a bit later :)
            new CopyWebpackPlugin([
                {
                    from: path.resolve(__dirname, 'node_modules/web-animations-js'),
                    to: path.join(CHANNELSTREAM_STATIC, 'web-animations-js')
                },
                {
                    from: path.resolve(__dirname, 'node_modules/@channelstream/channelstream/src'),
                    to: path.join(CHANNELSTREAM_STATIC, 'channelstream')
                },
                {
                    from: '**/*.js',
                    context: path.resolve(__dirname, 'node_modules/@webcomponents/webcomponentsjs'),
                    to: path.join(CHANNELSTREAM_STATIC, 'webcomponentsjs')
                },
                {
                    from: path.resolve(__dirname, 'node_modules/@babel/polyfill'),
                    to: path.join(CHANNELSTREAM_STATIC, '@babel/polyfill')
                },
                {
                    from: path.resolve(__dirname, 'dist/'),
                    to: path.join(CHANNELSTREAM_STATIC, '')
                }
            ])
            // new webpackUglifyJsPlugin({
            //     cacheFolder: path.resolve(__dirname, 'public/cached_uglify/'),
            //     debug: true,
            //     minimize: true,
            //     sourceMap: false,
            //     output: {
            //         comments: false
            //     },
            //     compressor: {
            //         warnings: false
            //     }
            // })
        ]
    }
};
let modernBabelConfig = {
    presets: [
        ["@babel/preset-env", {
            targets: {
                esmodules: true
            },
            modules: false,
            debug: true
        }]
    ],
    plugins: ["@babel/plugin-proposal-object-rest-spread", "transform-regenerator"]
};

let legacyBabelConfig = {
    presets: [
        ["@babel/preset-env", {
            targets: {
                browsers: ['IE 11']
            },
            modules: false,
            debug: true
        }]
    ],
    plugins: ["@babel/plugin-proposal-object-rest-spread", "transform-regenerator"]
};

let modernConfig = configFactory('modern', suffix = '', babelConfig = modernBabelConfig);
let legacyConfig = configFactory('legacy', suffix = 'es5', babelConfig = legacyBabelConfig);

module.exports = [modernConfig, legacyConfig];
