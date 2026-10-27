export class HttpClient {
    #networkTimeOut = 7000; // 7s to abort

    async get(path, params) {

        // Build URL relative to the page, so the app also works under a path
        // prefix (e.g. behind the data space gateway at /waste-collection/)
        const url = new URL(path, document.baseURI);

        const searchParams = new URLSearchParams(params);

        try {
            // Create abort controller to handle timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.#networkTimeOut);

            // Fetch with timeout
            const response = await fetch(url.toString() + '?' + searchParams.toString(), { signal: controller.signal });
            clearTimeout(timeoutId);

            if (response.status >= 200 && response.status <= 299) {
                const jsonResponse = await response.json();
                return jsonResponse;
            } else {
                // Handle errors
                console.error(response.status, response.statusText);
                return { error: response.statusText }
            }
        } catch (error) {
            // Timeout error
            return { error: "Request timeout" }
        }
    }
}