interface User {
    id: number;
    name: string;
    email: string;
    createdAt: Date;
}

interface ValidationResult {
    isValid: boolean;
    errors: string[];
}

// Validates user email format
function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Creates a new user with validation
function createUser(name: string, email: string): User | null {
    if (!validateEmail(email)) {
        return null;
    }

    return {
        id: Math.floor(Math.random() * 10000),
        name,
        email,
        createdAt: new Date()
    };
}

// Validates user data
function validateUser(user: User): ValidationResult {
    const errors: string[] = [];

    if (!user.name || user.name.length < 2) {
        errors.push("Name must be at least 2 characters long");
    }

    if (!validateEmail(user.email)) {
        errors.push("Invalid email format");
    }

    return {
        isValid: errors.length === 0,
        errors
    };
}

// Updates user information
function updateUser(user: User, updates: Partial<User>): User {
    return {
        ...user,
        ...updates
    };
}

// Formats user data for display
function formatUserData(user: User): string {
    return `User ${user.name} (${user.email}) - Created: ${user.createdAt.toLocaleDateString()}`;
}

// Dummy search function
function searchUsers(users: User[], query: string): User[] {
    return users.filter(user => 
        user.name.toLowerCase().includes(query.toLowerCase()) ||
        user.email.toLowerCase().includes(query.toLowerCase())
    );
}

// Example usage
const dummyUser = createUser("John Doe", "john@example.com");
if (dummyUser) {
    const validation = validateUser(dummyUser);
    console.log(validation.isValid ? "User is valid" : validation.errors.join(", "));
    
    const updatedUser = updateUser(dummyUser, { name: "John Smith" });
    console.log(formatUserData(updatedUser));
}
