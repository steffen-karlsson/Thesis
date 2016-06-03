package dk.steffenkarlsson.sofa.bdae.recycler;

import android.content.Context;
import android.support.v7.widget.RecyclerView;
import android.util.AttributeSet;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public abstract class RecyclerAdapter<T extends RecyclerAdapter.ViewModel> extends RecyclerView.Adapter<RecyclerAdapter.ViewHolder> {

    private final String TAG = getClass().getSimpleName();

    protected Context _context;

    protected List<T> items = new ArrayList<T>();
    protected Map<String, Integer> classMapping = new HashMap<>();
    private List<Class<? extends View>> viewClasses = new ArrayList<>();
    private Map<T, Integer> _uniqueIds = new HashMap<>();
    private int _id = 0;

    public static class ViewHolder extends RecyclerView.ViewHolder {
        public ViewHolder(View v) {
            super(v);
        }
    }

    public RecyclerAdapter(Context context) {
        _context = context;
    }

    public void add(int index, T item) {
        items.add(index, item);
        addViewClass(item.getClass().getName(), item.getViewClass());
        addUniqueId(item);
    }

    public void add(T item) {
        items.add(item);
        addViewClass(item.getClass().getName(), item.getViewClass());
        addUniqueId(item);
    }

    public void addViewClass(String className, Class<? extends View> viewClass) {
        if (!viewClasses.contains(viewClass)) {
            viewClasses.add(viewClass);
            classMapping.put(className, viewClasses.size() - 1);
        }
    }

    protected void addUniqueId(T item) {
        if (!_uniqueIds.containsKey(item)) {
            _uniqueIds.put(item, ++_id);
        }
    }

    public void add(T[] items) {
        for (T item : items) {
            add(item);
            addUniqueId(item);
        }
    }

    public List<T> getItems() {
        return items;
    }

    public void remove(T item) {
        items.remove(item);

        if (_uniqueIds.containsKey(item)) {
            _uniqueIds.remove(item);
        }
    }

    public void clear() {
        items.clear();
        viewClasses.clear();
        classMapping.clear();
    }

    public T getItem(int position) {
        return items != null ? items.get(position) : null;
    }

    @Override
    public int getItemCount() {
        return items != null ? items.size() : 0;
    }

    @Override
    public long getItemId(int position) {
        return _uniqueIds.get(getItem(position));
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        Class[] cArg = new Class[2]; // The constructor has 2 arguments
        cArg[0] = Context.class;
        cArg[1] = AttributeSet.class;

        Class<? extends View> viewClass = viewClasses.get(viewType);

        try {
            View view = (View) viewClass.getDeclaredConstructor(cArg).newInstance(parent.getContext(), null);

            ViewGroup.LayoutParams params = new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
            view.setLayoutParams(params);
            return new ViewHolder(view);
        } catch (InstantiationException e) {
            Log.e(TAG, "InstantiationException: " + viewClass.getSimpleName() + ". Make sure you have a constructer with (Context, AttributeSet)");
            return null;
        } catch (IllegalAccessException e) {
            Log.e(TAG, "IllegalAccessException: " + viewClass.getSimpleName() + ". Field or method not accessible");
            return null;
        } catch (NoSuchMethodException e) {
            Log.e(TAG, "NoSuchMethodException: " + viewClass.getSimpleName() + ". Method doesn't exist");
            return null;
        } catch (InvocationTargetException e) {
            Log.e(TAG, "InvocationTargetException: " + viewClass.getSimpleName() + ". Method could not be invoked");
            return null;
        }
    }

    @Override
    public int getItemViewType(int position) {
        return classMapping.get(getItem(position).getClass().getName());
    }

    public static abstract class ViewModel<V extends View> {
        public ViewModel() {
        }

        public abstract Class<V> getViewClass();

        public abstract void bind(V var1);
    }
}
