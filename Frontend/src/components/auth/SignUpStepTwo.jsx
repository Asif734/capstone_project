import React, { useState } from 'react';

const SignUpStepTwo = ({ onSubmit, onBack, regId }) => {
  const [formData, setFormData] = useState({
    otp: '',
    password: '',
    confirm_password: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Include reg_id from step one
    onSubmit({
      reg_id: regId,
      ...formData
    });
  };

  return (
    <div className="space-y-4">
      <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 mb-4">
        <p className="text-sm text-purple-200">OTP has been sent to your email</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-purple-200 mb-2">
          OTP
        </label>
        <input
          type="text"
          name="otp"
          value={formData.otp}
          onChange={handleChange}
          maxLength="6"
          className="w-full px-4 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-500 transition-colors"
          placeholder="Enter 6-digit OTP"
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

      <div>
        <label className="block text-sm font-medium text-purple-200 mb-2">
          Confirm Password
        </label>
        <input
          type="password"
          name="confirm_password"
          value={formData.confirm_password}
          onChange={handleChange}
          className="w-full px-4 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-500 transition-colors"
          placeholder="••••••••"
        />
      </div>

      <div className="flex space-x-3">
        <button
          onClick={onBack}
          className="flex-1 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all font-medium"
        >
          Back
        </button>
        <button
          onClick={handleSubmit}
          className="flex-1 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-purple-500/50 font-medium"
        >
          Sign Up
        </button>
      </div>
    </div>
  );
};

export default SignUpStepTwo;
