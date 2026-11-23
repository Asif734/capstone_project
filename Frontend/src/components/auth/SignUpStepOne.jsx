import React, { useState } from 'react';

const SignUpStepOne = ({ onNext, onSwitchToSignIn }) => {
  const [formData, setFormData] = useState({
    reg_id: '',
    email: '',
    consent_accepted: false,
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onNext({ ...formData, consent_accepted: true });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-purple-200 mb-2">
          Registration ID
        </label>
        <input
          type="text"
          name="reg_id"
          value={formData.reg_id}
          onChange={handleChange}
          required
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
          required
          className="w-full px-4 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-500 transition-colors"
          placeholder="your@email.com"
        />
      </div>

      <section
        aria-labelledby="data-consent-heading"
        className="space-y-3 rounded-lg border border-purple-500/30 bg-slate-900/60 p-4 text-sm text-purple-100"
      >
        <div>
          <h3 id="data-consent-heading" className="font-semibold text-white">
            Student Chatbot Conversation & Wellbeing Data Consent
          </h3>
          <p className="mt-1 text-xs text-purple-200">
            Please read how your information is used before creating an account.
          </p>
        </div>
        <div className="max-h-40 space-y-3 overflow-y-auto pr-2 leading-relaxed">
          <p>
            <strong>Information collected:</strong> We collect your registration ID,
            email address, messages, chatbot replies, and interaction timestamps.
            When you are signed in, conversations are associated with your account.
          </p>
          <p>
            <strong>How it is used:</strong> Conversations are stored to provide
            chatbot features and conversation continuity. Automated systems analyze
            messages to guide supportive responses and identify possible wellbeing
            concerns. Authorized administrators may review wellbeing alerts and
            related information. Conversation data may also be used to evaluate and
            improve the chatbot&apos;s quality, usefulness, and safety.
          </p>
          <p>
            <strong>Automated analysis:</strong> This analysis can be inaccurate,
            is not a medical or psychological diagnosis, and is not a substitute
            for professional care. The chatbot is not an emergency service.
          </p>
          <p>
            <strong>Storage:</strong> The application keeps recent conversations
            according to its configured limit (100 interactions per user by
            default). This is a storage limit, not a fixed deletion schedule.
            Account information and wellbeing alerts may remain stored while
            maintained by the service.
          </p>
          <p>
            <strong>Model training:</strong> The current service uses a pre-built
            wellbeing model and does not train or fine-tune it using saved
            conversations.
          </p>
          <p>
            Agreement is required to create an account. If you do not agree, do not
            continue with signup. You may stop using the service at any time; for
            questions or data requests, contact the service administrator.
          </p>
        </div>
        <label className="flex cursor-pointer items-start gap-3 border-t border-purple-500/20 pt-3">
          <input
            type="checkbox"
            name="consent_accepted"
            checked={formData.consent_accepted}
            onChange={handleChange}
            required
            className="mt-1 h-4 w-4 shrink-0 accent-purple-500"
          />
          <span>
            I have read and agree to the Student Chatbot Conversation &amp;
            Wellbeing Data Consent.
          </span>
        </label>
      </section>

      <button
        type="submit"
        className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-purple-500/50 font-medium"
      >
        Send OTP
      </button>

      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={onSwitchToSignIn}
          className="text-purple-300 hover:text-white transition-colors text-sm"
        >
          Already have an account? Sign in
        </button>
      </div>
    </form>
  );
};

export default SignUpStepOne;