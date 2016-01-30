require('es6-promise').polyfill()
var webpack = require('webpack')

module.exports = {
    context: __dirname + "/frontend",
    entry: {
        app: "./src/main.jsx",
        bootstrap: "bootstrap-webpack!./src/bootstrap.config.js"
    },
    output: {
        path: __dirname + "/src/webpack",
        filename: "[name].js"
    },
    module: {
        loaders: [
            // **IMPORTANT** This is needed so that each bootstrap js file required by
            // bootstrap-webpack has access to the jQuery object
            { test: /bootstrap\/js\//, loader: 'imports?jQuery=jquery' },
            {
                test: /\.jsx$/,
                exclude: /node_modules/,
                loader: "babel",
                query: {presets:['react', 'es2015']}
            },
            {
                test: /\.(woff|woff2)$/,
                loader: "url-loader?limit=10000&mimetype=application/font-woff"
            },
            { test: /\.css$/, loader: 'style-loader!css-loader' },
            { test: /\.ttf$/,    loader: "file-loader" },
            { test: /\.eot$/,    loader: "file-loader" },
            { test: /\.svg$/,    loader: "file-loader" }
      ],
    },
    // plugins: [
    //     new webpack.optimize.UglifyJsPlugin({
    //         minimize: true,
    //         compress: { warnings: false }}
    //     )
    // ]
};