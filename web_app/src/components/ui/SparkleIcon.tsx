import { SVGProps } from 'react';

interface SparkleIconProps extends SVGProps<SVGSVGElement> {
  className?: string;
}

export const SparkleIcon = ({ className = '', ...props }: SparkleIconProps) => {
  return (
    <svg
      xmlns='http://www.w3.org/2000/svg'
      width='16'
      height='16'
      viewBox='0 0 16 16'
      fill='none'
      className={className}
      {...props}
    >
      <path
        d='M2 8C6.17867 8 8 6.242 8 2C8 6.242 9.80867 8 14 8C9.80867 8 8 9.80867 8 14C8 9.80867 6.17867 8 2 8Z'
        fill='white'
        stroke='white'
        strokeWidth='1.5'
        strokeLinejoin='round'
      />
    </svg>
  );
};
