import * as React from 'react';
import { Button, Icon } from 'semantic-ui-react';

interface Props {}

export default function PlaybackControls(_: Props): React.ReactElement {
  const [isPlaying, setIsPlaying] = React.useState(false);

  const toggleIsPlaying = React.useCallback(() => setIsPlaying(!isPlaying), [
    isPlaying
  ]);

  return (
    <Button.Group>
      <Button icon>
        <Icon name="backward" />
      </Button>
      <Button icon onClick={toggleIsPlaying}>
        <Icon name={isPlaying ? 'pause' : 'play'} />
      </Button>
      <Button icon>
        <Icon name="forward" />
      </Button>
    </Button.Group>
  );
}
