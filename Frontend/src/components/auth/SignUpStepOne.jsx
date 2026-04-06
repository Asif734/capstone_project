import React, { useState } from 'react';

const SignUpStepOne = ({ onNext, onSwitchToSignIn }) => {
  const [formData, setFormData] = useState({
    reg_id: '',
    email: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onNext(formData);
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
          placeholder="Enter your registration ID"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-purple-200 mb-2">
          Email
        </label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className="w-full px-4 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-500 transition-colors"
          placeholder="your@email.com"
        />
      </div>

      <button
        onClick={handleSubmit}
        className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-purple-500/50 font-medium"
      >
        Send OTP
      </button>

      <div className="mt-6 text-center">
        <button
          onClick={onSwitchToSignIn}
          className="text-purple-300 hover:text-white transition-colors text-sm"
        >
          Already have an account? Sign in
        </button>
      </div>
    </div>
  );
};

export default SignUpStepOne;