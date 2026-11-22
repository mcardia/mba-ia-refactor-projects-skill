function createUserService({ db, userModel, enrollmentModel, paymentModel }) {
    return {
        // Removes the user together with their payments and enrollments (no orphan rows).
        deleteUser(userId) {
            return db.transaction(async () => {
                await paymentModel.deleteByUserId(userId);
                await enrollmentModel.deleteByUserId(userId);
                return userModel.deleteById(userId);
            });
        },
    };
}

module.exports = { createUserService };
