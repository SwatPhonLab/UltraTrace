import * as React from 'react';

import { Button, Icon, Input } from 'semantic-ui-react';

type Props = {
  placeholder: string;
};

export default function SeekableSelector({
  placeholder,
}: Props): React.ReactElement {
  return (
    <div className="flex">
      <Button className="ph3" icon>
        <Icon name="fast backward" />
      </Button>
      <Button className="ph3" icon>
        <Icon name="backward" />
      </Button>
      <Input className="ph3" placeholder={placeholder} />
      <Button className="ph3" icon>
        <Icon name="forward" />
      </Button>
      <Button className="ph3" icon>
        <Icon name="fast forward" />
      </Button>
    </div>
  );
}
