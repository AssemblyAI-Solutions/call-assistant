export default async function handler(req, res) {
    if (req.method === 'POST') {
        const { url, session_id } = req.body;
        // add validation logic if required

        // Make your request here
        // You can use fetch, axios, or any other request library you prefer
        try {
            const response = await fetch('PORT 5001 NGROK URL HERE', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, session_id }),
            });

            if (!response.ok) {
                console.log(response)
                throw new Error(`An error occurred: ${response.statusText}`);
            }

            const data = await response.json();
            res.status(200).json(data);
        } catch (error) {
            console.log(error.message)
            res.status(500).json({ error: error.message || 'An error occurred' });
        }
    } else {
        // Handle any other HTTP method
        res.setHeader('Allow', ['POST']);
        res.status(405).json({ message: `Method ${req.method} is not allowed` });
    }
}