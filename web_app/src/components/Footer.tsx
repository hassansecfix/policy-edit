import { FeedbackButton } from './FeedbackButton';
import { FooterDescription } from './FooterDescription';

interface FooterProps {
  feedbackHref?: string;
  email?: string;
}

export const Footer = ({ feedbackHref, email }: FooterProps) => {
  return (
    <footer className='flex flex-col gap-4 items-center justify-start w-full py-8 px-6'>
      <div className='flex items-center justify-center'>
        <FeedbackButton href={feedbackHref} email={email} />
      </div>
      <div className='w-full max-w-lg'>
        <FooterDescription />
      </div>
    </footer>
  );
};
