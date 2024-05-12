export default async function handler(req, res) {
    if (req.method === 'GET') {
        const { session_id } = req.query;
        console.log("RUNNNING")
        // add validation logic if required

        // Make your request here
        // You can use fetch, axios, or any other request library you prefer
        try {
            const response = await fetch(`https://PORT5000URL HERE/stream_id?session_id=${session_id}`, { // need to update url
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });

            if (!response.ok) {
                throw new Error(`An error occurred: ${response.statusText}`);
            }

            const data = await response.json();
            res.status(200).json(data);
        } catch (error) {
            res.status(500).json({ error: error.message || 'An error occurred' });
        }
    } else {
        // Handle any other HTTP method
        res.setHeader('Allow', ['POST']);
        res.status(405).json({ message: `Method ${req.method} is not allowed` });
    }
}