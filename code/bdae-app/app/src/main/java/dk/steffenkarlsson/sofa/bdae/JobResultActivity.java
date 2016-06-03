package dk.steffenkarlsson.sofa.bdae;

import android.os.Bundle;
import android.webkit.WebView;

import java.util.ArrayList;
import java.util.List;

import butterknife.BindView;
import dk.steffenkarlsson.sofa.bdae.extra.DataTypeHelper;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public class JobResultActivity extends BaseConfigurationActivity {

    private static final List<String> SUPPORTED_TYPES = new ArrayList<String>() {{
        add("img");
    }};

    private static final String KEY_TITLE = "KEY_TITLE";
    private static final String KEY_RESULT = "KEY_RESULT";
    private static final String KEY_DATA_TYPE = "KEY_DATA_TYPE";

    @BindView(R.id.webView)
    protected WebView mResultView;

    @Override
    protected void onResume() {
        super.onResume();

        if (getSupportActionBar() != null)
            getSupportActionBar().setHomeAsUpIndicator(R.drawable.ic_clear_white);

        mActivityHandler.setActionbarTitle(getIntent().getStringExtra(KEY_TITLE));

        mResultView.getSettings().setJavaScriptEnabled(true);
        mResultView.getSettings().setLoadWithOverviewMode(true);
        mResultView.getSettings().setUseWideViewPort(true);
        mResultView.getSettings().setBuiltInZoomControls(true);
        mResultView.getSettings().setDisplayZoomControls(false);
        mResultView.loadDataWithBaseURL("", DataTypeHelper.getHTML(
                getActivity(),
                getIntent().getStringExtra(KEY_RESULT),
                getIntent().getStringExtra(KEY_DATA_TYPE)), "text/html", "UTF-8", "");
    }

    @Override
    protected boolean requiresConfiguration() {
        return true;
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.activity_job_result;
    }

    @Override
    protected int getTitleResource() {
        return -1;
    }

    @Override
    protected boolean showBackButton() {
        return true;
    }

    public static boolean isSupported(String dataType) {
        return SUPPORTED_TYPES.contains(dataType);
    }

    public static Bundle getBundleArgs(String title, String result, String dataType) {
        Bundle bundle = new Bundle();
        bundle.putString(KEY_TITLE, title);
        bundle.putString(KEY_RESULT, result);
        bundle.putString(KEY_DATA_TYPE, dataType);
        return bundle;
    }
}
