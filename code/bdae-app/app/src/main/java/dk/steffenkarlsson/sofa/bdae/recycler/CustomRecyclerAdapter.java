package dk.steffenkarlsson.sofa.bdae.recycler;

import android.content.Context;
import android.support.v7.widget.GridLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.view.View;

/**
 * Created by steffenkarlsson on 4/13/16.
 */
public class CustomRecyclerAdapter extends RecyclerAdapter<GenericRecyclerViewModel> {

    private final RecyclerView _view;

    private boolean _itemsSelectable;
    private View.OnClickListener _onClickListener;

    public CustomRecyclerAdapter(Context context, RecyclerView view) {
        super(context);
        this._view = view;
    }

    public void setItemsSelectable(boolean selectable) {
        if (_itemsSelectable != selectable) {
            _itemsSelectable = selectable;
            notifyDataSetChanged();
        }
    }

    public void setItemClickListener(View.OnClickListener onClickListener) {
        _onClickListener = onClickListener;
    }

    @Override
    public void onBindViewHolder(ViewHolder holder, int position) {

        final GenericRecyclerViewModel item = getItem(position);
        item.extBind((BaseRecyclerView) holder.itemView, _view.getLayoutManager() instanceof GridLayoutManager);

        item.setSelectable(_itemsSelectable);
        if (_onClickListener != null) item.setOnItemClickListener(_onClickListener);
    }

    public void add(int index, GenericRecyclerViewModel item) {
        items.add(index, item);
        addViewClass(item.getData().getClass().getName(), item.getViewClass());
        addUniqueId(item);
    }

    public void add(GenericRecyclerViewModel item) {
        items.add(item);
        addViewClass(item.getData().getClass().getName(), item.getViewClass());
        addUniqueId(item);
    }

    @Override
    public void add(GenericRecyclerViewModel[] items) {
        throw new UnsupportedOperationException();
    }

    public int getPositionForItem(Object item) {
        int count = getItemCount();
        for (int position = 0; position < count; position++) {
            if (getItem(position).equals(item)) {
                return position;
            }
        }

        return -1;
    }

    @Override
    public int getItemViewType(int position) {
        return classMapping.get(getItem(position).getData().getClass().getName());
    }
}
