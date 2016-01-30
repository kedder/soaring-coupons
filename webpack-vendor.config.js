var webpack = require('webpack')

module.exports = {
    context: __dirname + "/frontend",
    entry: {
        vendor: [
            'jquery',
            'react',
            'react-dom',
            'react-time',
            'react-bootstrap',
            "bootstrap-webpack!./src/bootstrap.config.js"
        ]
    },
    output: {
        path: __dirname + "/src/webpack",
        library: "[name]_[hash]",
        filename: "[name].js"
    },
    module: {
        loaders: [
            // **IMPORTANT** This is needed so that each bootstrap js file required by
            // bootstrap-webpack has access to the jQuery object
            { test: /bootstrap\/js\//, loader: 'imports?jQuery=jquery' },
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
    plugins: [
        new webpack.DllPlugin({
            path: __dirname + "/frontend/manifest/[name]-manifest.json",
            name: "[name]_[hash]"
        }),
        new webpack.optimize.UglifyJsPlugin({
            minimize: true,
            compress: { warnings: false }}
        )
    ]
};
