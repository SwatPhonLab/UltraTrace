import * as React from 'react';

import { Button, Icon, Table } from 'semantic-ui-react';
import { Seq } from 'immutable';
import { uuid } from 'uuidv4';
import TraceSelectorRow, { TraceItem } from './TraceSelectorRow';

type Props = {
  traces: Seq.Indexed<
    React.ReactElement<
      React.ComponentProps<typeof TraceSelectorRow>,
      typeof TraceSelectorRow
    >
  >;
  onAddTrace: (item: TraceItem) => void;
};

/**
 * The list of traces. Provides an interface to modify the trace list.
 */
export default function TraceSelector({
  traces,
  onAddTrace,
}: Props): React.ReactElement {
  const addTrace = React.useCallback(() => {
    onAddTrace({ id: uuid(), name: '', color: 'blue' });
  }, [onAddTrace]);
  return (
    <Table selectable>
      <Table.Body>{traces}</Table.Body>
      <Table.Footer>
        <Table.HeaderCell colSpan="3">
          <Button.Group>
            <Button icon>
              <Icon name="minus" />
            </Button>
            <Button icon>
              <Icon name="plus" onClick={addTrace} />
            </Button>
          </Button.Group>
        </Table.HeaderCell>
      </Table.Footer>
    </Table>
  );
}
