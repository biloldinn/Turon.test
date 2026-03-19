const mongoose = require('mongoose');

const MONGO_URI = 'mongodb+srv://biloldin07:biloldin07@cluster0.pvnge.mongodb.net/turon_test?retryWrites=true&w=majority';

async function migrate() {
    try {
        await mongoose.connect(MONGO_URI);
        console.log('Connected to MongoDB');

        const TestSchema = new mongoose.Schema({
            startTime: Date,
            endTime: Date
        });
        const Test = mongoose.model('Test', TestSchema);

        const result = await Test.updateMany({}, { $set: { startTime: null, endTime: null } });
        console.log(`Migration successful! Updated ${result.modifiedCount} tests.`);

        await mongoose.disconnect();
        process.exit(0);
    } catch (err) {
        console.error('Migration failed:', err);
        process.exit(1);
    }
}

migrate();
