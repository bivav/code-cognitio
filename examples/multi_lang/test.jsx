import React, { useState } from 'react';

const UserForm = ({ onSubmit, initialData = {} }) => {
  const [name, setName] = useState(initialData.name || '');
  const [email, setEmail] = useState(initialData.email || '');
  const [error, setError] = useState('');

  const validateEmail = (email) => {
    return email.includes('@') && email.split('@')[1].includes('.');
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setError('');

    if (!name) {
      setError('Name is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Invalid email format');
      return;
    }

    onSubmit({ name, email });
  };

  return (
    <div className="user-form">
      <h2>User Information</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Name:</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <button type="submit">Save User</button>
      </form>
    </div>
  );
};

export default UserForm;
