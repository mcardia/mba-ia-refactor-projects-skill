const { parseCheckoutPayload } = require('./validators');

function createCheckoutController({ checkoutService }) {
    return {
        async create(req, res) {
            const input = parseCheckoutPayload(req.body);
            const { enrollmentId } = await checkoutService.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
