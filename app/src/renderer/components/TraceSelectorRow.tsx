import * as React from 'react';

import {
  Button,
  CheckboxProps,
  Input,
  InputOnChangeData,
  Radio,
  SemanticCOLORS,
  Table,
} from 'semantic-ui-react';

type Props = {
  key: string;
  item: TraceItem;
  onEditItem: (nextItem: TraceItem) => void;
  isSelected: boolean;
  onSelect: (data: CheckboxProps) => void;
};

export interface TraceItem {
  id: string;
  name: string;
  color: SemanticCOLORS;
}

/**
 * A single trace. Provides an interface to edit the trace's metadata.
 */
export default function TraceSelectorRow({
  item,
  onEditItem,
  isSelected,
  onSelect,
}: Props): React.ReactElement {
  // State of the name input while the user has it focused
  const [inflightName, setInflightName] = React.useState(item.name);

  const commitNameChange = React.useCallback(
    () => onEditItem({ ...item, name: inflightName }),
    [item, inflightName],
  );
  const updateInflightName = React.useCallback(
    (_: React.ChangeEvent, data: InputOnChangeData) =>
      setInflightName(data.value),
    [],
  );

  const onRadioChange = React.useCallback(
    (_: React.FormEvent, data: CheckboxProps) => onSelect(data),
    [],
  );

  return (
    <Table.Row>
      <Table.Cell>
        <Radio
          label=""
          checked={isSelected}
          value={item.id}
          onChange={onRadioChange}
        />
      </Table.Cell>
      <Table.Cell>
        <Input
          defaultValue={item.name}
          // When the user unfocuses the input element, we're going to fire off
          // the callback passed in props to edit the item in the list of traces
          onBlur={commitNameChange}
          onChange={updateInflightName}
        />
      </Table.Cell>
      <Table.Cell>
        <Button color={item.color} />
      </Table.Cell>
    </Table.Row>
  );
}
