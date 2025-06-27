
const path = require('path');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  mode: process.env.NODE_ENV || 'development',
  entry: './src/index.js',
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: process.env.NODE_ENV === 'production' 
      ? '[name].[contenthash].js' 
      : '[name].js',
    chunkFilename: process.env.NODE_ENV === 'production'
      ? '[name].[contenthash].chunk.js'
      : '[name].chunk.js',
    clean: true,
  },

  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
        },
      },
    },
    runtimeChunk: 'single',
  },

  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },

  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-env',
              '@babel/preset-react',
              '@babel/preset-typescript',
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader'],
      },
    ],
  },

  plugins: [
    ...(process.env.ANALYZE_BUNDLE ? [new BundleAnalyzerPlugin()] : []),
  ],

  devServer: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: 'all',
    historyApiFallback: true,
    compress: true,
  },
};
