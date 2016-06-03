package dk.steffenkarlsson.sofa.bdae.extra;

import android.support.v4.app.Fragment;
import android.view.View;

import java.util.HashMap;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class ViewCache {
    private HashMap<Integer, ICacheableView> mViewMap = new HashMap<>();

    private static ViewCache ourInstance = new ViewCache();

    public static ViewCache getInstance() {
        return ourInstance;
    }

    private ViewCache() {
    }

    public void putView(int identifier, ICacheableView view) {
        if (!hasView(identifier))
            mViewMap.put(identifier, view);
    }

    public boolean hasView(int identifier) {
        return mViewMap.containsKey(identifier);
    }

    public ICacheableView getView(int identifier) {
        return hasView(identifier) ? mViewMap.get(identifier) : null;
    }

    public void deleteView(int identifier) {
        if (hasView(identifier))
            mViewMap.remove(identifier);
    }

    public static interface ICacheableView {
        boolean shouldCache();
        View getRoot();
    }
}
