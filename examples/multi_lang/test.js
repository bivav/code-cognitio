/**
 * Sample JavaScript file for testing multi-language support.
 */

/**
 * Represents a user in the system.
 */
class User {
  /**
   * Initialize a new user.
   * @param {string} name - The user's name
   * @param {string} email - The user's email
   */
  constructor(name, email) {
    this.name = name;
    this.email = email;
  }

  /**
   * Check if the email is valid.
   * @returns {boolean} True if valid, False otherwise
   */
  validateEmail() {
    return this.email.includes('@') && this.email.split('@')[1].includes('.');
  }
}

/**
 * Create a new user.
 * @param {string} name - The user's name
 * @param {string} email - The user's email
 * @returns {User} A new User instance
 * @throws {Error} If the email is invalid
 */
function createUser(name, email) {
  const user = new User(name, email);
  if (!user.validateEmail()) {
    throw new Error(`Invalid email: ${email}`);
  }
  return user;
}

try {
  const user = createUser('John Doe', 'john@example.com');
  console.log(`Created user ${user.name} with email ${user.email}`);
} catch (error) {
  console.error(`Error: ${error.message}`);
}
