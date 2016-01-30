var webpack = require('webpack')

module.exports = {
    context: __dirname + "/frontend",
    entry: {
        app: ["./src/main.jsx"],
    },
    output: {
        path: __dirname + "/src/webpack",
        filename: "[name].js"
    },
    module: {
        loaders: [
            {
                test: /\.jsx$/,
                exclude: /node_modules/,
                loader: "babel",
                query: {presets:['react', 'es2015']}
            },
            { test: /\.css$/, loader: 'style-loader!css-loader' },
      ],
    },
    plugins: [
        new webpack.DllReferencePlugin({
            context: __dirname + '/frontend',
            manifest: require(__dirname + "/var/vendor-manifest.json")
        }),
    ]
};
