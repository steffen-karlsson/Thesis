package dk.steffenkarlsson.sofa.bdae;

import android.os.Bundle;
import android.support.annotation.IdRes;
import android.support.annotation.Nullable;
import android.support.v4.view.PagerAdapter;
import android.support.v4.view.ViewPager;
import android.util.SparseIntArray;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;

import com.roughike.bottombar.BottomBar;
import com.roughike.bottombar.OnMenuTabClickListener;

import java.util.HashMap;

import butterknife.Bind;
import dk.steffenkarlsson.sofa.bdae.extra.ViewCache;
import dk.steffenkarlsson.sofa.bdae.view.BottomBarConfigureView;
import dk.steffenkarlsson.sofa.bdae.view.BottomBarDashboardView;
import dk.steffenkarlsson.sofa.bdae.view.BottomBarDataView;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class MainActivity extends BaseActivity {

    private static final int PAGE_DASHBOARD = 0;
    private static final int PAGE_DATA = 1;
    private static final int PAGE_CONFIGURE = 2;

    @Bind(R.id.pager)
    protected ViewPager mPager;

    @Bind(R.id.container)
    protected FrameLayout mContainer;

    private BottomBar mBottomBar;
    private BottomBarPagerAdapter mAdapter;

    private ViewCache mViewCache = ViewCache.getInstance();

    private SparseIntArray mPositionMapper = new SparseIntArray() {{
        put(R.id.bottombar_dashboard, 0);
        put(R.id.bottombar_data, 1);
        put(R.id.bottombar_configuration, 2);
    }};

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mBottomBar = BottomBar.attach(mContainer, savedInstanceState);
        mBottomBar.noTopOffset();
        mBottomBar.useOnlyStatusBarTopOffset();
        mBottomBar.hideShadow();
        mBottomBar.noNavBarGoodness();
        mBottomBar.setMaxFixedTabs(2);
        mBottomBar.setItemsFromMenu(R.menu.bottombar, mOnMenuTabClickListener);
    }

    @Override
    protected void onResume() {
        super.onResume();

        mAdapter = new BottomBarPagerAdapter();
        mPager.setAdapter(mAdapter);
        mPager.addOnPageChangeListener(mOnPageChangeListener);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);

        mBottomBar.onSaveInstanceState(outState);
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.activity_main;
    }

    @Override
    protected int getTitleResource() {
        return R.string.app_name_long;
    }

    private ViewPager.OnPageChangeListener mOnPageChangeListener = new ViewPager.OnPageChangeListener() {
        @Override
        public void onPageScrolled(int position, float positionOffset, int positionOffsetPixels) { }

        @Override
        public void onPageSelected(int position) {
            mBottomBar.setDefaultTabPosition(position);
        }

        @Override
        public void onPageScrollStateChanged(int state) { }
    };

    private OnMenuTabClickListener mOnMenuTabClickListener = new OnMenuTabClickListener() {
        @Override
        public void onMenuTabSelected(@IdRes int menuItemId) {
            selectPage(menuItemId);
        }

        @Override
        public void onMenuTabReSelected(@IdRes int menuItemId) {
            selectPage(menuItemId);
        }
    };

    private void selectPage(int menuItemId) {
        if (mAdapter != null)
            mPager.setCurrentItem(mPositionMapper.get(menuItemId));
    }

    private class BottomBarPagerAdapter extends PagerAdapter {

        @Override
        public int getCount() {
            return 3;
        }

        @Override
        public boolean isViewFromObject(View view, Object object) {
            return view == object;
        }

        @Override
        public Object instantiateItem(ViewGroup container, int position) {
            ViewCache.ICacheableView view = null;

            if (mViewCache.hasView(position))
                view = mViewCache.getView(position);
            else {
                switch (position) {
                    case PAGE_DASHBOARD:
                        view = new BottomBarDashboardView(getApplicationContext());
                        break;
                    case PAGE_DATA:
                        view = new BottomBarDataView(getApplicationContext());
                        break;
                    case PAGE_CONFIGURE:
                        view = new BottomBarConfigureView(getApplicationContext());
                        break;
                    default:
                        break;
                }
            }

            if (view != null) {
                if (view.shouldCache())
                    mViewCache.putView(position, view);

                container.addView(view.getRoot());
                return view;
            }
            return null;
        }

        @Override
        public void destroyItem(ViewGroup container, int position, Object object) {
            container.removeView((View) object);
        }

        @Override
        public int getItemPosition(Object object) {
            return POSITION_NONE;
        }
    }
}