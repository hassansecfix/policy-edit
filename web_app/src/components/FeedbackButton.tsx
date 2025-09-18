interface FeedbackButtonProps {
  href?: string;
  email?: string;
}

export const FeedbackButton = ({
  href = 'https://secfix.typeform.com/to/ZgKXUZkR#email=hassan@secfix.com&source=my-tasks',
  email = 'hassan@secfix.com',
}: FeedbackButtonProps) => {
  const feedbackUrl = href.includes('#email=') ? href : `${href}#email=${email}&source=my-tasks`;

  return (
    <a
      href={feedbackUrl}
      target='_blank'
      rel='noopener noreferrer'
      className='flex items-center justify-center gap-2.5 px-2 pb-2 group'
    >
      <span className='font-medium text-sm text-violet-600 text-center whitespace-nowrap group-hover:underline underline-offset-2'>
        Share feedback about this page
      </span>
    </a>
  );
};
