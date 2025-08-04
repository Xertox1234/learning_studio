const path = require('path');

module.exports = {
  entry: {
    'codemirror-enhanced': './static/js/codemirror6-enhanced.js',
    'codemirror-themes': './static/js/codemirror-themes.js',
    'react-app': './frontend/src/main.jsx'
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, 'static/js/dist'),
    library: '[name]',
    libraryTarget: 'umd',
    globalObject: 'this'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    modules: ['node_modules'],
    extensions: ['.js', '.jsx', '.css']
  },
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  devtool: process.env.NODE_ENV === 'production' ? false : 'source-map'
};