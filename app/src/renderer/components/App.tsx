import * as React from 'react';

import { Responsive, Segment } from 'semantic-ui-react';

import { TraceItem } from './TraceSelectorRow';
import Sidebar from './Sidebar';
import Window from './Window';

interface Props {}

export default function App(_: Props): React.ReactElement {
  const [currentTrace, setCurrentTrace] = React.useState<TraceItem | null>(
    null,
  );
  return (
    <Segment.Group horizontal>
      <Responsive
        as={Sidebar}
        currentTrace={currentTrace}
        setCurrentTrace={setCurrentTrace}
      />
      <Responsive as={Window} currentTrace={currentTrace} />
    </Segment.Group>
  );
}
