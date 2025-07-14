/** @typedef {import("express").Request} Request */
/** @typedef {import("express").Response} Response */
/** @typedef {import("express").NextFunction} NextFunction */

/**
 * Express error handler middleware.
 * @param {Error & {status?: number}} err
 * @param {Request} req
 * @param {Response} res
 * @param {NextFunction} next
 */
export default (err, req, res, next) => {
    console.error(err);
    res.status(err.status || 500).json({
        message: err.message || 'Internal Server Error',
    });
};