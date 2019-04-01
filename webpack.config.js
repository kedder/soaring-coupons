var webpack = require('webpack')

module.exports = {
    mode: 'development',
    context: __dirname + "/frontend",
    entry: {
        app: ["./src/main.jsx"],
    },
    output: {
        path: __dirname + "/src/webpack",
        filename: "[name].js"
    },
    module: {
        rules: [
            {
                test: /\.jsx$/,
                exclude: /node_modules/,
                loader: "babel-loader",
                query: {presets:['@babel/react', '@babel/env']}
            },
            { test: /\.css$/, loader: 'style-loader!css-loader' },
      ],
    },
    plugins: [
        new webpack.DllReferencePlugin({
            context: __dirname + '/frontend',
            manifest: require(__dirname + "/frontend/manifest/vendor-manifest.json")
        }),
    ]
};
