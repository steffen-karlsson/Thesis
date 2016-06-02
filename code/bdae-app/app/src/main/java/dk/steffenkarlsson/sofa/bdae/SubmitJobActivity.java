package dk.steffenkarlsson.sofa.bdae;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class SubmitJobActivity extends BaseConfigurationActivity {

    @Override
    protected void onResume() {
        super.onResume();

        if(getSupportActionBar() != null)
            getSupportActionBar().setHomeAsUpIndicator(R.drawable.ic_clear_white);
    }

    @Override
    protected boolean requiresConfiguration() {
        return true;
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.activity_submit_job;
    }

    @Override
    protected boolean showBackButton() {
        return true;
    }

    @Override
    protected int getTitleResource() {
        return R.string.actionbar_submit_job;
    }
}
