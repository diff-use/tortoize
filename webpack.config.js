const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const path = require('path');

const SCRIPTS = path.resolve(__dirname, "webapp");
const SCSS = path.resolve(__dirname, "scss");
const DEST = path.resolve(__dirname, "docroot/scripts");

module.exports = (env) => {

	const PRODUCTION = env != null && env.PRODUCTION;

	const webpackConf = {
		entry: {
			'pdb-redo-style': path.resolve(SCSS, "pdb-redo-bootstrap.scss"),
			'index': path.resolve(SCRIPTS, 'index.js')
		},

		output: {
			path: DEST,
			clean: true
		},

		module: {
			rules: [
				{
					test: /\.js/,
					exclude: /node_modules/,
					use: {
						loader: "babel-loader",
						options: {
							presets: ['@babel/preset-env']
						}
					}
				},
				{
					test: /\.(eot|svg|ttf|woff(2)?)(\?v=\d+\.\d+\.\d+)?/,
					loader: 'file-loader',
					options: {
						name: '[name].[ext]',
						outputPath: 'fonts/',
						publicPath: '../fonts/'
					}
				},
				{
					test: /\.(sa|sc|c)ss$/i,
					use: [
						MiniCssExtractPlugin.loader,
						"css-loader",
						"postcss-loader",
						"sass-loader"
					]
				},

				{
					test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
					include: path.resolve(__dirname, './node_modules/bootstrap-icons/font/fonts'),
					type: 'asset/resource',
					generator: {
						filename: '../fonts/[name][ext]'
					}
				},

				{
					test: /\.png$/,
					type: 'asset/resource',
					generator: {
						filename: '../images/[name][ext]'
					}
				}
			]
		},

		resolve: {
			extensions: ['.js', '.scss'],
		},

		plugins: [
			new MiniCssExtractPlugin({
				filename: "../css/[name].css"
			}),
			new CleanWebpackPlugin({
				verbose: true,
				cleanOnceBeforeBuildPatterns: [
					path.resolve(__dirname, 'scripts'),
					path.resolve(__dirname, 'fonts')
				]
			})],

		optimization: { minimizer: [] }
	};

	if (PRODUCTION) {
		webpackConf.mode = "production";

		webpackConf.optimization.minimizer.push(
			new TerserPlugin({ /* additional options here */ }),
			new UglifyJsPlugin({ parallel: 4 })
		);
	} else {
		webpackConf.mode = "development";
		webpackConf.devtool = 'source-map';
		webpackConf.plugins.push(new webpack.optimize.AggressiveMergingPlugin())
	}

	return webpackConf;
};
