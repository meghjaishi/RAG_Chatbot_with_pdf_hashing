export interface LoginResponse {
    access_token: string;
    token_type: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function login(
    username: string,
    password: string
): Promise<LoginResponse> {
    const body = new URLSearchParams();

    body.append("username", username);
    body.append("password", password);

    const response = await fetch(
        `${API_BASE_URL}/auth/login`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body,
        }
    );

    if (!response.ok) {
        throw new Error("Invalid username or password");
    }

    return response.json();
}
