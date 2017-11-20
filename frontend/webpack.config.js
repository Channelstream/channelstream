var HtmlWebpackPlugin = require('html-webpack-plugin');
var CopyWebpackPlugin = require('copy-webpack-plugin');
var webpackUglifyJsPlugin = require('webpack-uglify-js-plugin');
var path = require('path');

module.exports = {
    // Tell Webpack which file kicks off our app.
    entry: {
        admin: path.resolve(__dirname, 'src/channelstream-admin/index.js'),
        demo: path.resolve(__dirname, 'src/channelstream-demo/index.js')
    },
    // Tell Weback to output our bundle to ./dist/bundle.js
    output: {
        filename: 'channelstream-[name].js',
        path: path.resolve(__dirname, '..', 'channelstream', 'static')
    },
    // Tell Webpack which directories to look in to resolve import statements.
    // Normally Webpack will look in node_modules by default but since we’re overriding
    // the property we’ll need to tell it to look there in addition to the
    // bower_components folder.
    resolve: {
        modules: [
            path.resolve(__dirname, 'node_modules'),
            path.resolve(__dirname, 'bower_components')
        ]
    },
    // These rules tell Webpack how to process different module types.
    // Remember, *everything* is a module in Webpack. That includes
    // CSS, and (thanks to our loader) HTML.
    module: {
        rules: [
            {
                // If you see a file that ends in .html, send it to these loaders.
                test: /\.html$/,
                // This is an example of chained loaders in Webpack.
                // Chained loaders run last to first. So it will run
                // polymer-webpack-loader, and hand the output to
                // babel-loader. This let's us transpile JS in our `<script>` elements.
                use: [
                    {loader: 'babel-loader'},
                    {loader: 'polymer-webpack-loader'}
                ]
            },
            {
                // If you see a file that ends in .js, just send it to the babel-loader.
                test: /\.js$/,
                use: 'babel-loader'
                // Optionally exclude node_modules from transpilation except for polymer-webpack-loader:
                // exclude: /node_modules\/(?!polymer-webpack-loader\/).*/
            },
            {
                test: /\polymer-redux.html/,
                use: 'exports-loader?PolymerRedux'
            },
            {
                test: /\polymer-redux.js/,
                use: 'exports-loader?PolymerRedux'
            }
        ]
    },
    plugins: [
        // This plugin will copy files over to ‘./dist’ without transforming them.
        // That's important because the custom-elements-es5-adapter.js MUST
        // remain in ES2015. We’ll talk about this a bit later :)
        new CopyWebpackPlugin([{
            from: path.resolve(__dirname, 'bower_components/webcomponentsjs/*.js'),
            to: 'bower_components/webcomponentsjs/[name].[ext]'
        }]),
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
};
