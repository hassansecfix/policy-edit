import Image from 'next/image';

export function Header() {
  return (
    <header className='flex items-center'>
      <div className='flex items-center py-1'>
        <Image
          src='/company_logo_default.png'
          alt='Secfix Logo'
          className='h-5 w-auto'
          width={80}
          height={20}
        />
      </div>
    </header>
  );
}
