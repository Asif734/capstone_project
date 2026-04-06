// import React, { useState } from 'react';
// import { X } from 'lucide-react';
// import SignInForm from './SignInForm';
// import SignUpStepOne from './SignUpStepOne';
// import SignUpStepTwo from './SignUpStepTwo';

// const AuthModal = ({ isOpen, onClose, initialMode = 'signin' }) => {
//   const [authMode, setAuthMode] = useState(initialMode);
//   const [signupStep, setSignupStep] = useState(1);
//   const [signupData, setSignupData] = useState({});

//   if (!isOpen) return null;

//   const handleSignInSubmit = (data) => {
//     console.log('Sign In:', data);
//     // TODO: Call API for sign in
//     // onClose();
//   };

//   const handleSignUpStepOne = (data) => {
//     setSignupData(data);
//     console.log('Sign Up Step 1:', data);
//     // TODO: Call API to send OTP
//     setSignupStep(2);
//   };

//   const handleSignUpStepTwo = (data) => {
//     console.log('Sign Up Step 2:', data);
//     // TODO: Call API for sign up with OTP
//     // onClose();
//   };

//   const handleBack = () => {
//     setSignupStep(1);
//   };

//   const switchToSignUp = () => {
//     setAuthMode('signup');
//     setSignupStep(1);
//   };

//   const switchToSignIn = () => {
//     setAuthMode('signin');
//     setSignupStep(1);
//   };

//   const getTitle = () => {
//     if (authMode === 'signin') return 'Welcome Back';
//     return signupStep === 1 ? 'Create Account' : 'Verify & Set Password';
//   };

//   return (
//     <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
//       <div className="bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full border border-purple-500/30 relative">
//         <button
//           onClick={onClose}
//           className="absolute top-4 right-4 text-purple-300 hover:text-white transition-colors"
//         >
//           <X className="w-6 h-6" />
//         </button>

//         <div className="p-8">
//           <h2 className="text-2xl font-bold text-white mb-6">{getTitle()}</h2>

//           {authMode === 'signin' && (
//             <SignInForm
//               onSubmit={handleSignInSubmit}
//               onSwitchToSignUp={switchToSignUp}
//             />
//           )}

//           {authMode === 'signup' && signupStep === 1 && (
//             <SignUpStepOne
//               onNext={handleSignUpStepOne}
//               onSwitchToSignIn={switchToSignIn}
//             />
//           )}

//           {authMode === 'signup' && signupStep === 2 && (
//             <SignUpStepTwo
//               onSubmit={handleSignUpStepTwo}
//               onBack={handleBack}
//               regId={signupData.reg_id}
//             />
//           )}
//         </div>
//       </div>
//     </div>
//   );
// };

// export default AuthModal;




import React, { useState } from 'react';
import { X } from 'lucide-react';
import SignInForm from './SignInForm';
import SignUpStepOne from './SignUpStepOne';
import SignUpStepTwo from './SignUpStepTwo';

const AuthModal = ({
  isOpen,
  onClose,
  initialMode = 'signin',
  signIn,
  sendOTP,
  verifyOTP,
  error,
}) => {
  const [authMode, setAuthMode] = useState(initialMode);
  const [signupStep, setSignupStep] = useState(1);
  const [signupData, setSignupData] = useState({});

  // Update authMode when initialMode changes
  React.useEffect(() => {
    if (isOpen) {
      setAuthMode(initialMode);
      setSignupStep(1);
    }
  }, [isOpen, initialMode]);

  if (!isOpen) return null;

  const handleSignInSubmit = (data) => {
    signIn(data).then((res) => {
      if (res.success) {
        onClose();
      }
    });
  };

  const handleSignUpStepOne = (data) => {
    setSignupData(data);
    sendOTP(data).then((res) => {
      if (res.success) {
        setSignupStep(2);
      }
    });
  };

  const handleSignUpStepTwo = (data) => {
    verifyOTP(data).then((res) => {
      if (res.success) {
        onClose();
      }
    });
  };

  const handleBack = () => {
    setSignupStep(1);
  };

  const switchToSignUp = () => {
    setAuthMode('signup');
    setSignupStep(1);
  };

  const switchToSignIn = () => {
    setAuthMode('signin');
    setSignupStep(1);
  };

  const getTitle = () => {
    if (authMode === 'signin') return 'Welcome Back';
    return signupStep === 1 ? 'Create Account' : 'Verify & Set Password';
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full border border-purple-500/30 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-purple-300 hover:text-white transition-colors"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="p-8">
          <h2 className="text-2xl font-bold text-white mb-6">{getTitle()}</h2>
          {error && (
            <div className="mb-4 rounded-lg border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          )}

          {authMode === 'signin' && (
            <SignInForm
              onSubmit={handleSignInSubmit}
              onSwitchToSignUp={switchToSignUp}
            />
          )}

          {authMode === 'signup' && signupStep === 1 && (
            <SignUpStepOne
              onNext={handleSignUpStepOne}
              onSwitchToSignIn={switchToSignIn}
            />
          )}

          {authMode === 'signup' && signupStep === 2 && (
            <SignUpStepTwo
              onSubmit={handleSignUpStepTwo}
              onBack={handleBack}
              regId={signupData.reg_id}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
