package dk.steffenkarlsson.sofa.bdae.view;

import android.app.Activity;
import android.content.Context;
import android.graphics.PorterDuff;
import android.support.annotation.IdRes;
import android.support.v7.app.AppCompatActivity;
import android.text.Editable;
import android.util.AttributeSet;
import android.view.MenuItem;
import android.view.View;

import com.rengwuxian.materialedittext.MaterialEditText;

import butterknife.BindView;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.extra.ConfigurationHandler;
import dk.steffenkarlsson.sofa.bdae.extra.ChangedTextWatcher;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class BottomBarConfigureView extends BasePagerControllerView {

    @BindView(R.id.inputInstanceName)
    protected MaterialEditText mInputInstanceName;

    @BindView(R.id.inputApiHostname)
    protected MaterialEditText mInputApiHostname;

    @BindView(R.id.inputGateway)
    protected MaterialEditText mInputGateway;

    private boolean mConfigurationHasChanged = false;
    private Activity mActivity;

    public BottomBarConfigureView(Context context) {
        super(context);
    }

    public BottomBarConfigureView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    private ChangedTextWatcher.OnValidateListener mOnValidateListener = new ChangedTextWatcher.OnValidateListener() {
        @Override
        public void onValidated(int index, boolean isValid, boolean hasChanged) {
            if (hasChanged && isValid) {
                mConfigurationHasChanged = true;
                ((AppCompatActivity) mActivity).supportInvalidateOptionsMenu();
            }
        }

        @Override
        public boolean validate(MaterialEditText editText, Editable s) {
            return ChangedTextWatcher.emptyValidator(editText, s);
        }
    };

    @Override
    public boolean hasOptionsMenu() {
        return true;
    }

    @Override
    public void setContent(Activity activity) {
        this.mActivity = activity;
        ConfigurationHandler handler = ConfigurationHandler.getInstance();

        mInputInstanceName.setText(handler.getInstanceName());
        mInputApiHostname.setText(handler.getApiHostName());
        mInputGateway.setText(handler.getGateway(false));

        mInputInstanceName.addTextChangedListener(new ChangedTextWatcher(mInputInstanceName, -1, mOnValidateListener));
        mInputGateway.addTextChangedListener(new ChangedTextWatcher(mInputGateway, -1, mOnValidateListener));
        mInputApiHostname.addTextChangedListener(new ChangedTextWatcher(mInputApiHostname, 1, new ChangedTextWatcher.OnValidateListener() {
            @Override
            public void onValidated(int index, boolean isValid, boolean hasChanged) {
                mOnValidateListener.onValidated(index, isValid, hasChanged);
            }

            @Override
            public boolean validate(MaterialEditText editText, Editable s) {
                return ChangedTextWatcher.ipPortValidator(editText, s);
            }
        }));
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.content_configure_view;
    }

    @Override
    public boolean shouldCache() {
        return true;
    }

    @Override
    public int getOptionsMenuRes() {
        return R.menu.accept;
    }

    @Override
    public void onOptionsMenuClicked(@IdRes int menuId) {
        super.onOptionsMenuClicked(menuId);
    }

    @Override
    public void onModifyMenuItem(MenuItem menuItem) {
        super.onModifyMenuItem(menuItem);

        menuItem.getIcon().setColorFilter(getResources().getColor(mConfigurationHasChanged
                ? R.color.white
                : R.color.colorPrimaryDark), PorterDuff.Mode.SRC_ATOP);
    }

    @Override
    public View getRoot() {
        return this;
    }
}
