import * as React from 'react';

import { Button, Icon, Input } from 'semantic-ui-react';

interface Props {
  placeholder: string;
}

export default function SeekableSelector({
  placeholder,
}: Props): React.ReactElement {
  return (
    <div>
      <Button icon>
        <Icon name="fast backward" />
      </Button>
      <Button icon>
        <Icon name="backward" />
      </Button>
      <Input placeholder={placeholder} />
      <Button icon>
        <Icon name="forward" />
      </Button>
      <Button icon>
        <Icon name="fast forward" />
      </Button>
    </div>
  );
}
