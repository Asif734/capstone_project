import React, { useState } from 'react';

const SignInForm = ({ onSubmit, onSwitchToSignUp }) => {
  const [formData, setFormData] = useState({
    reg_id: '',
    password: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-purple-200 mb-2">
          Registration ID
        </label>
        <input
          type="text"
          name="reg_id"
          value={formData.reg_id}
          onChange={handleChange}
          className="w-full px-4 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-500 transition-colors"
          placeholder="Your registration ID"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-purple-200 mb-2">
          Password
        </label>
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          className="w-full px-4 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-500 transition-colors"
          placeholder="••••••••"
        />
      </div>

      <button
        onClick={handleSubmit}
        className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-purple-500/50 font-medium"
      >
        Sign In
      </button>

      <div className="mt-6 text-center">
        <button
          onClick={onSwitchToSignUp}
          className="text-purple-300 hover:text-white transition-colors text-sm"
        >
          Don't have an account? Sign up
        </button>
      </div>
    </div>
  );
};

export default SignInForm;
