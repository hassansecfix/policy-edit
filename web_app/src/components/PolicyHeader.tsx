import { Badge } from './ui/Badge';

const PolicyHeader = () => {
  return (
    <div className='text-center mb-8 px-4'>
      <h2 className='text-base font-medium text-gray-700 mb-2'>
        POL-11 Access Control <Badge>Beta</Badge>
      </h2>

      <h2 className='text-xl font-semibold text-gray-900 mb-2'>Policy scoping questionnaire</h2>

      <p className='text-sm text-gray-500 max-w-xl mx-auto font-medium'>
        Answer the following questions to configure your policy. This information will be used to
        generate a customized policy document for your organization.
      </p>
    </div>
  );
};

export { PolicyHeader };
